#include "Jinking.h"
#include <cmath>

namespace Action
{
	PortsList Jinking::providedPorts()
	{
		return {
			InputPort<CPPBlackBoard*>("BB"),
			InputPort<double>("Freq", 3.0, "jink frequency (rad/s scale)")
		};
	}

	NodeStatus Jinking::tick()
	{
		Optional<CPPBlackBoard*> BB = getInput<CPPBlackBoard*>("BB");
		double w = getInput<double>("Freq").value();

		Vector3 my = (*BB)->MyLocation_Cartesian;
		Vector3 F = (*BB)->MyForwardVector; F.normalize();
		Vector3 R = (*BB)->MyRightVector;   R.normalize();
		Vector3 U = (*BB)->MyUpVector;      U.normalize();

		double t = (*BB)->RunningTime;

		// 좌우/상하 이위상 진동 -> 예측 불가한 저크
		double lat = std::sin(t * w);
		double vert = std::sin(t * w * 1.37 + 1.1);

		(*BB)->VP_Cartesian = my + F * 3000.0 + R * (4000.0 * lat) + U * (2000.0 * vert);

		return NodeStatus::SUCCESS;
	}
}
